# Update the upgrade_subscription route
@app.route('/subscription/upgrade', methods=['POST'])
@login_required
def upgrade_subscription():
    """Create Stripe checkout session for premium subscription."""
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=current_user.email,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'DreamLoop Premium',
                        'description': 'Unlimited AI dream analysis and advanced features',
                    },
                    'unit_amount': 999,  # $9.99 in cents
                    'recurring': {
                        'interval': 'month',
                    },
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.host_url + url_for('subscription') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + url_for('subscription'),
            metadata={
                'user_email': current_user.email,
                'user_id': current_user.id
            }
        )
        
        return redirect(checkout_session.url, code=303)
        
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        flash('An error occurred during checkout. Please try again.')
        return redirect(url_for('subscription'))
